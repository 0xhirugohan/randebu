import { writable } from 'svelte/store';
import type { Bot } from '$lib/api';

export const currentBotStore = writable<Bot | null>(null);

export function setCurrentBot(bot: Bot | null) {
	currentBotStore.set(bot);
}

export function clearCurrentBot() {
	currentBotStore.set(null);
}
