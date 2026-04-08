import { writable } from 'svelte/store';
import type { BotConversation } from '$lib/api';

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: Date;
}

export const chatStore = writable<ChatMessage[]>([]);

export function addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
	const newMessage: ChatMessage = {
		...message,
		id: crypto.randomUUID(),
		timestamp: new Date()
	};
	chatStore.update(messages => [...messages, newMessage]);
}

export function setMessages(messages: BotConversation[]) {
	chatStore.set(messages.map(m => ({
		id: m.id,
		role: m.role,
		content: m.content,
		timestamp: new Date(m.created_at)
	})));
}

export function clearChat() {
	chatStore.set([]);
}
