import { writable } from 'svelte/store';
import type { Backtest, BacktestResult } from '$lib/api';

export interface BacktestState {
	currentBacktest: Backtest | null;
	backtestHistory: Backtest[];
	isLoading: boolean;
	error: string | null;
}

const initialState: BacktestState = {
	currentBacktest: null,
	backtestHistory: [],
	isLoading: false,
	error: null
};

export const backtestStore = writable<BacktestState>(initialState);

export function setCurrentBacktest(backtest: Backtest | null) {
	backtestStore.update(state => ({ ...state, currentBacktest: backtest }));
}

export function addBacktestToHistory(backtest: Backtest) {
	backtestStore.update(state => ({
		...state,
		backtestHistory: [backtest, ...state.backtestHistory]
	}));
}

export function setBacktestHistory(backtests: Backtest[]) {
	backtestStore.update(state => ({ ...state, backtestHistory: backtests }));
}

export function setBacktestLoading(loading: boolean) {
	backtestStore.update(state => ({ ...state, isLoading: loading }));
}

export function setBacktestError(error: string | null) {
	backtestStore.update(state => ({ ...state, error }));
}

export function clearBacktestState() {
	backtestStore.set(initialState);
}
