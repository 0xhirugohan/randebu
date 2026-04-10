/**
 * Simple markdown parser for rendering AI responses
 * Supports: bold, italic, code blocks, inline code, links, lists, tables, headings, line breaks
 */

interface InlineSegment {
	type: 'text' | 'bold' | 'italic' | 'code' | 'link';
	content: string;
	href?: string;
}

interface ParsedSegment {
	type: 'text' | 'bold' | 'italic' | 'code' | 'codeBlock' | 'link' | 'list' | 'table' | 'lineBreak' | 'heading';
	content: string;
	items?: string[];
	headers?: InlineSegment[][];
	rows?: InlineSegment[][];
}

export function parseMarkdown(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	// Normalize line endings
	text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
	
	// First, extract code blocks
	const codeBlockRegex = /```[\s\S]*?```/g;
	const parts = text.split(codeBlockRegex);
	const codeBlocks = text.match(codeBlockRegex) || [];
	
	let partIndex = 0;
	
	while (partIndex < parts.length) {
		const part = parts[partIndex];
		
		if (part.trim()) {
			// Process non-code content
			segments.push(...parseInlineContent(part));
		}
		
		// Add code block if there's one after this part
		if (partIndex < codeBlocks.length) {
			const codeContent = codeBlocks[partIndex].replace(/^```\w*\n?/, '').replace(/```$/, '');
			segments.push({ type: 'codeBlock', content: codeContent });
		}
		
		partIndex++;
	}
	
	return segments;
}

function parseInlineContent(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	// Check for tables first
	const tableRegex = /^\|.+\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)*)/gm;
	let tableMatch;
	while ((tableMatch = tableRegex.exec(text)) !== null) {
		// Add content before table
		const beforeTable = text.substring(0, tableMatch.index);
		if (beforeTable.trim()) {
			segments.push(...parseLines(beforeTable));
		}
		
		// Parse table
		const tableContent = tableMatch[0];
		const tableSegments = parseTable(tableContent);
		segments.push(...tableSegments);
		
		// Update text for next iteration
		text = text.substring(tableMatch.index + tableContent.length);
	}
	
	// Add remaining content
	if (text.trim()) {
		segments.push(...parseLines(text));
	}
	
	return segments;
}

function parseTable(tableStr: string): ParsedSegment[] {
	const lines = tableStr.trim().split('\n').filter(line => line.trim());
	if (lines.length < 2) return [];
	
	// Skip separator line (|---|---|)
	const dataLines = lines.filter(line => !line.match(/^[\|\s\-:]+$/));
	if (dataLines.length < 2) return [];
	
	const headers = parseTableRow(dataLines[0]);
	const rows = dataLines.slice(1).map(row => parseTableRow(row));
	
	return [{
		type: 'table',
		content: '',
		headers,
		rows
	}];
}

function parseTableRow(row: string): InlineSegment[][] {
	return row.split('|')
		.map(cell => cell.trim())
		.filter(cell => cell !== '')
		.map(cell => parseInlineElements(cell));
}

function parseInlineElements(text: string): InlineSegment[] {
	const segments: InlineSegment[] = [];
	
	const inlineRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[.*?\]\(.*?\))/g;
	const parts = text.split(inlineRegex);
	
	for (const part of parts) {
		if (!part) continue;
		
		if (part.startsWith('**') && part.endsWith('**')) {
			segments.push({ type: 'bold', content: part.slice(2, -2) });
		} else if (part.startsWith('*') && part.endsWith('*')) {
			segments.push({ type: 'italic', content: part.slice(1, -1) });
		} else if (part.startsWith('`') && part.endsWith('`')) {
			segments.push({ type: 'code', content: part.slice(1, -1) });
		} else if (part.startsWith('[') && part.includes('](')) {
			const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
			if (linkMatch) {
				segments.push({ type: 'link', content: linkMatch[1], href: linkMatch[2] });
			}
		} else if (part) {
			segments.push({ type: 'text', content: part });
		}
	}
	
	return segments;
}

// Render inline segments to HTML string
function renderInlineSegments(segments: InlineSegment[]): string {
	return segments.map(seg => {
		switch (seg.type) {
			case 'bold': return `<strong>${seg.content}</strong>`;
			case 'italic': return `<em>${seg.content}</em>`;
			case 'code': return `<code class="inline-code">${seg.content}</code>`;
			case 'link': return `<a href="${seg.href || '#'}" target="_blank" rel="noopener noreferrer">${seg.content}</a>`;
			default: return seg.content;
		}
	}).join('');
}

function parseLines(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	// Combined regex for inline formatting
	const inlineRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[.*?\]\(.*?\))/g;
	const lines = text.split('\n');
	
	for (let i = 0; i < lines.length; i++) {
		const line = lines[i];
		
		if (!line.trim()) {
			// Empty line - add line break for paragraph separation
			segments.push({ type: 'lineBreak', content: '' });
			continue;
		}
		
		// Check for headings
		if (line.match(/^#{1,6}\s/)) {
			segments.push({ type: 'heading', content: line.replace(/^#+\s/, '') });
			continue;
		}
		
		// Check for list items
		if (line.match(/^[\-\*]\s/)) {
			const listMatch = line.match(/^([\-\*])\s(.*)/);
			if (listMatch) {
				// Parse inline formatting for list item
				const itemContent = listMatch[2];
				const inlineSegments = parseInlineElements(itemContent);
				
				// Check if previous segment is a list
				const lastSeg = segments[segments.length - 1];
				if (lastSeg && lastSeg.type === 'list') {
					lastSeg.items?.push(itemContent);
				} else {
					segments.push({ type: 'list', content: '', items: [itemContent] });
				}
			}
			continue;
		}
		
		// Check for numbered lists
		if (line.match(/^\d+\.\s/)) {
			const listMatch = line.match(/^\d+\.\s(.*)/);
			if (listMatch) {
				const itemContent = listMatch[1];
				
				const lastSeg = segments[segments.length - 1];
				if (lastSeg && lastSeg.type === 'list') {
					lastSeg.items?.push(itemContent);
				} else {
					segments.push({ type: 'list', content: '', items: [itemContent] });
				}
			}
			continue;
		}
		
		// Process inline formatting
		const inlineSegments = parseInlineElementsAsText(line);
		segments.push(...inlineSegments);
		
		// Add line break after non-empty lines (except last in a paragraph)
		if (i < lines.length - 1 && line.trim()) {
			segments.push({ type: 'lineBreak', content: '' });
		}
	}
	
	return segments;
}

function parseInlineElementsAsText(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	const inlineRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[.*?\]\(.*?\))/g;
	const parts = text.split(inlineRegex);
	
	for (const part of parts) {
		if (!part) continue;
		
		if (part.startsWith('**') && part.endsWith('**')) {
			segments.push({ type: 'bold', content: part.slice(2, -2) });
		} else if (part.startsWith('*') && part.endsWith('*')) {
			segments.push({ type: 'italic', content: part.slice(1, -1) });
		} else if (part.startsWith('`') && part.endsWith('`')) {
			segments.push({ type: 'code', content: part.slice(1, -1) });
		} else if (part.startsWith('[') && part.includes('](')) {
			const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
			if (linkMatch) {
				segments.push({ type: 'link', content: linkMatch[1] });
			}
		} else if (part) {
			segments.push({ type: 'text', content: part });
		}
	}
	
	return segments;
}
