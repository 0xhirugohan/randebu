import { writable } from 'svelte/store';
import type { Simulation, Signal } from '$lib/api';

export interface KlineData {
	time: number;
	close: number;
}

export interface TradeLogEntry {
	time: number;
	price: number;
	action: 'buy' | 'sell' | 'hold';
	reason: string;
	position: number;
	entry_price: number | null;
}

export interface Portfolio {
	initial_balance: number;
	current_balance: number;
	position: number;
	position_token: string;
	entry_price: number;
	current_price: number;
}

export interface SimulationState {
	currentSimulation: Simulation | null;
	signals: Signal[];
	klines: KlineData[];
	tradeLog: TradeLogEntry[];
	portfolio: Portfolio;
	isLoading: boolean;
	error: string | null;
}

const initialState: SimulationState = {
	currentSimulation: null,
	signals: [],
	klines: [],
	tradeLog: [],
	portfolio: {
		initial_balance: 10000,
		current_balance: 10000,
		position: 0,
		position_token: '',
		entry_price: 0,
		current_price: 0
	},
	isLoading: false,
	error: null
};

export const simulationStore = writable<SimulationState>(initialState);

export function setCurrentSimulation(simulation: Simulation | null) {
	simulationStore.update(state => ({ 
		...state, 
		currentSimulation: simulation,
		klines: simulation?.klines || [],
		tradeLog: simulation?.trade_log || [],
		portfolio: simulation?.portfolio || state.portfolio
	}));
}

export function updatePortfolio(portfolio: Partial<Portfolio>) {
	simulationStore.update(state => ({
		...state,
		portfolio: { ...state.portfolio, ...portfolio }
	}));
}

export function addSignals(newSignals: Signal[]) {
	simulationStore.update(state => ({
		...state,
		signals: [...state.signals, ...newSignals]
	}));
}

export function clearSignals() {
	simulationStore.update(state => ({ ...state, signals: [] }));
}

export function setSimulationLoading(loading: boolean) {
	simulationStore.update(state => ({ ...state, isLoading: loading }));
}

export function setSimulationError(error: string | null) {
	simulationStore.update(state => ({ ...state, error }));
}

export function clearSimulationState() {
	simulationStore.set(initialState);
}
