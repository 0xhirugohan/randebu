/**
 * Simple markdown parser for rendering AI responses
 * Supports: bold, italic, code blocks, inline code, links, lists, headings
 */

interface ParsedSegment {
	type: 'text' | 'bold' | 'italic' | 'code' | 'codeBlock' | 'link' | 'list';
	content: string;
	items?: string[];
}

export function parseMarkdown(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	// Split by code blocks first (they can contain other markdown)
	const codeBlockRegex = /```[\s\S]*?```/g;
	const parts = text.split(codeBlockRegex);
	const codeBlocks = text.match(codeBlockRegex) || [];
	
	let partIndex = 0;
	
	while (partIndex < parts.length) {
		const part = parts[partIndex];
		
		if (part) {
			// Process inline formatting
			segments.push(...parseInlineMarkdown(part));
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

function parseInlineMarkdown(text: string): ParsedSegment[] {
	const segments: ParsedSegment[] = [];
	
	// Combined regex for bold, italic, inline code, links
	const inlineRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\\\[.*?\]\(.*?\))/g;
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
		} else if (part.includes('\n')) {
			// Handle newlines and lists
			const lines = part.split('\n');
			for (let i = 0; i < lines.length; i++) {
				const line = lines[i];
				if (line.match(/^[\-\*]\s/)) {
					// List item
					if (segments.length > 0 && segments[segments.length - 1].type === 'list') {
						segments[segments.length - 1].items?.push(line.slice(2));
					} else {
						segments.push({ type: 'list', content: '', items: [line.slice(2)] });
					}
				} else if (line.match(/^#{1,6}\s/)) {
					// Heading
					segments.push({ type: 'text', content: line });
				} else if (line) {
					if (i > 0) {
						segments.push({ type: 'text', content: '\n' + line });
					} else {
						segments.push({ type: 'text', content: line });
					}
				}
			}
		} else {
			segments.push({ type: 'text', content: part });
		}
	}
	
	return segments;
}
