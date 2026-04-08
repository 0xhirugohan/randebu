import { writable } from 'svelte/store';
import type { Simulation, Signal } from '$lib/api';

export interface SimulationState {
	currentSimulation: Simulation | null;
	signals: Signal[];
	isLoading: boolean;
	error: string | null;
}

const initialState: SimulationState = {
	currentSimulation: null,
	signals: [],
	isLoading: false,
	error: null
};

export const simulationStore = writable<SimulationState>(initialState);

export function setCurrentSimulation(simulation: Simulation | null) {
	simulationStore.update(state => ({ ...state, currentSimulation: simulation }));
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
