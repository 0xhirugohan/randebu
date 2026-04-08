import { writable } from 'svelte/store';
import type { User } from '$lib/api';

export const userStore = writable<User | null>(null);

export function setUser(user: User | null) {
	userStore.set(user);
}

export function clearUser() {
	userStore.set(null);
}
