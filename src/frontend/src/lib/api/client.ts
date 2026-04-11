import type {
	User,
	Bot,
	BotConversation,
	Backtest,
	Simulation,
	Signal,
	AuthResponse,
	BotChatRequest,
	BotChatResponse,
	StrategyConfig
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function getAuthHeaders(): HeadersInit {
	const token = localStorage.getItem('token');
	return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
		let errorMessage = 'An error occurred';
		
		if (typeof error.detail === 'string') {
			errorMessage = error.detail;
		} else if (Array.isArray(error.detail)) {
			// Handle FastAPI validation error format: [{type, loc, msg, input}]
			errorMessage = error.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
		} else if (error.message) {
			errorMessage = error.message;
		} else {
			errorMessage = `HTTP error ${response.status}`;
		}
		
		throw new Error(errorMessage);
	}
	return response.json();
}

export const api = {
	auth: {
		async register(email: string, password: string): Promise<AuthResponse> {
			const response = await fetch(`${API_URL}/auth/register`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
			return handleResponse<AuthResponse>(response);
		},

		async login(email: string, password: string): Promise<AuthResponse> {
			const response = await fetch(`${API_URL}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username: email, password })
			});
			return handleResponse<AuthResponse>(response);
		},

		async logout(): Promise<void> {
			await fetch(`${API_URL}/auth/logout`, {
				method: 'POST',
				headers: getAuthHeaders()
			});
		},

		async me(): Promise<User> {
			const response = await fetch(`${API_URL}/auth/me`, {
				headers: getAuthHeaders()
			});
			return handleResponse<User>(response);
		}
	},

	bots: {
		async list(): Promise<Bot[]> {
			const response = await fetch(`${API_URL}/bots`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Bot[]>(response);
		},

		async create(name: string, description?: string): Promise<Bot> {
			const response = await fetch(`${API_URL}/bots`, {
				method: 'POST',
				headers: getAuthHeaders(),
				body: JSON.stringify({ name, description })
			});
			return handleResponse<Bot>(response);
		},

		async get(id: string): Promise<Bot> {
			const response = await fetch(`${API_URL}/bots/${id}`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Bot>(response);
		},

		async update(id: string, data: Partial<Bot>): Promise<Bot> {
			const response = await fetch(`${API_URL}/bots/${id}`, {
				method: 'PUT',
				headers: getAuthHeaders(),
				body: JSON.stringify(data)
			});
			return handleResponse<Bot>(response);
		},

		async delete(id: string): Promise<void> {
			const response = await fetch(`${API_URL}/bots/${id}`, {
				method: 'DELETE',
				headers: getAuthHeaders()
			});
			if (!response.ok) {
				throw new Error(`HTTP error ${response.status}`);
			}
		},

		async chat(id: string, message: string, signal?: AbortSignal): Promise<BotChatResponse> {
			const response = await fetch(`${API_URL}/bots/${id}/chat`, {
				method: 'POST',
				headers: getAuthHeaders(),
				body: JSON.stringify({ message } as BotChatRequest),
				signal
			});
			return handleResponse<BotChatResponse>(response);
		},

		async getHistory(id: string): Promise<BotConversation[]> {
			const response = await fetch(`${API_URL}/bots/${id}/history`, {
				headers: getAuthHeaders()
			});
			return handleResponse<BotConversation[]>(response);
		}
	},

	backtest: {
		async start(botId: string, config: { token: string; timeframe: string; start_date: string; end_date: string }): Promise<Backtest> {
			const response = await fetch(`${API_URL}/bots/${botId}/backtest`, {
				method: 'POST',
				headers: getAuthHeaders(),
				body: JSON.stringify({ ...config, chain: 'bsc' })
			});
			return handleResponse<Backtest>(response);
		},

		async get(botId: string, runId: string): Promise<Backtest> {
			const response = await fetch(`${API_URL}/bots/${botId}/backtest/${runId}`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Backtest>(response);
		},

		async list(botId: string): Promise<Backtest[]> {
			const response = await fetch(`${API_URL}/bots/${botId}/backtests`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Backtest[]>(response);
		},

		async stop(botId: string, runId: string): Promise<void> {
			const response = await fetch(`${API_URL}/bots/${botId}/backtest/${runId}/stop`, {
				method: 'POST',
				headers: getAuthHeaders()
			});
			if (!response.ok) {
				throw new Error(`HTTP error ${response.status}`);
			}
		},

		async getTrades(botId: string, runId: string, page: number = 1, perPage: number = 5): Promise<{
			trades: any[];
			total_trades: number;
			page: number;
			per_page: number;
			total_pages: number;
			has_next: boolean;
			has_prev: boolean;
		}> {
			const response = await fetch(`${API_URL}/bots/${botId}/backtest/${runId}/trades?page=${page}&per_page=${perPage}`, {
				headers: getAuthHeaders()
			});
			if (!response.ok) {
				throw new Error(`HTTP error ${response.status}`);
			}
			return response.json();
		}
	},

	simulate: {
		async start(botId: string, config: { token: string; chain?: string; check_interval: number }): Promise<Simulation> {
			const response = await fetch(`${API_URL}/bots/${botId}/simulate`, {
				method: 'POST',
				headers: getAuthHeaders(),
				body: JSON.stringify(config)
			});
			return handleResponse<Simulation>(response);
		},

		async get(botId: string, runId: string): Promise<Simulation> {
			const response = await fetch(`${API_URL}/bots/${botId}/simulate/${runId}`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Simulation>(response);
		},

		async list(botId: string): Promise<Simulation[]> {
			const response = await fetch(`${API_URL}/bots/${botId}/simulations`, {
				headers: getAuthHeaders()
			});
			return handleResponse<Simulation[]>(response);
		},

		async stop(botId: string, runId: string): Promise<void> {
			const response = await fetch(`${API_URL}/bots/${botId}/simulate/${runId}/stop`, {
				method: 'POST',
				headers: getAuthHeaders()
			});
			if (!response.ok) {
				throw new Error(`HTTP error ${response.status}`);
			}
		}
	},

	config: {
		async getChains(): Promise<string[]> {
			const response = await fetch(`${API_URL}/config/chains`, {
				headers: getAuthHeaders()
			});
			return handleResponse<string[]>(response);
		},

		async getTokens(): Promise<{ symbol: string; chain: string; name: string }[]> {
			const response = await fetch(`${API_URL}/config/tokens`, {
				headers: getAuthHeaders()
			});
			return handleResponse<{ symbol: string; chain: string; name: string }[]>(response);
		}
	}
};
