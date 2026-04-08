import { writable } from 'svelte/store';
import type { Bot } from '$lib/api';

export const botsStore = writable<Bot[]>([]);

export function setBots(bots: Bot[]) {
	botsStore.set(bots);
}

export function addBot(bot: Bot) {
	botsStore.update(bots => [...bots, bot]);
}

export function updateBot(bot: Bot) {
	botsStore.update(bots => bots.map(b => b.id === bot.id ? bot : b));
}

export function removeBot(botId: string) {
	botsStore.update(bots => bots.filter(b => b.id !== botId));
}

export function clearBots() {
	botsStore.set([]);
}
