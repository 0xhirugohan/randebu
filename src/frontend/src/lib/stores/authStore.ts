import { writable, get } from 'svelte/store';
import { api } from '$lib/api';
import { setUser, clearUser, clearBots } from './index';
import { clearSimulationState } from './simulationStore';
import { clearBacktestState } from './backtestStore';

export const isAuthenticated = writable(false);
export const isLoading = writable(true);

export async function initAuth() {
	isLoading.set(true);
	const token = localStorage.getItem('token');
	if (token) {
		try {
			const user = await api.auth.me();
			setUser(user);
			isAuthenticated.set(true);
		} catch {
			localStorage.removeItem('token');
			isAuthenticated.set(false);
		}
	}
	isLoading.set(false);
}

export async function login(email: string, password: string) {
	const response = await api.auth.login(email, password);
	localStorage.setItem('token', response.access_token);
	const user = await api.auth.me();
	setUser(user);
	isAuthenticated.set(true);
}

export async function register(email: string, password: string) {
	const response = await api.auth.register(email, password);
	localStorage.setItem('token', response.access_token);
	const user = await api.auth.me();
	setUser(user);
	isAuthenticated.set(true);
}

export function logout() {
	api.auth.logout().catch(() => {});
	localStorage.removeItem('token');
	clearUser();
	clearBots();
	clearBacktestState();
	clearSimulationState();
	isAuthenticated.set(false);
}
