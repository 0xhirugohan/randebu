import { writable } from 'svelte/store';
import type { BotConversation } from '$lib/api';

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	thinking: string | null;
	timestamp: Date;
}

// Fallback UUID generator for environments where crypto.randomUUID is not available
function generateId(): string {
	if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
		return crypto.randomUUID();
	}
	// Fallback: simple UUID v4 implementation
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
		const r = (Math.random() * 16) | 0;
		const v = c === 'x' ? r : (r & 0x3) | 0x8;
		return v.toString(16);
	});
}

export const chatStore = writable<ChatMessage[]>([]);

export function addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
	const newMessage: ChatMessage = {
		...message,
		id: generateId(),
		timestamp: new Date()
	};
	chatStore.update(messages => [...messages, newMessage]);
}

export function setMessages(messages: BotConversation[]) {
	chatStore.set(messages.map(m => ({
		id: m.id,
		role: m.role,
		content: m.content,
		thinking: null,
		timestamp: new Date(m.created_at)
	})));
}

export function clearChat() {
	chatStore.set([]);
}
