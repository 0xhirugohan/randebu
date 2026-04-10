export interface User {
	id: string;
	email: string;
	created_at: string;
	updated_at: string;
}

export interface Bot {
	id: string;
	user_id: string;
	name: string;
	description: string | null;
	strategy_config: StrategyConfig;
	llm_config: LLMConfig;
	status: 'draft' | 'active' | 'paused';
	created_at: string;
	updated_at: string;
}

export interface StrategyConfig {
	conditions: Condition[];
	actions: Action[];
	risk_management?: RiskManagement;
}

export interface Condition {
	type: 'price_drop' | 'price_rise' | 'volume_spike' | 'price_level';
	token: string;
	token_address?: string;
	chain?: string;
	threshold?: number;
	price?: number;
	direction?: 'above' | 'below';
	timeframe?: string;
}

export interface Action {
	type: 'buy' | 'sell' | 'hold';
	amount_percent?: number;
	token?: string;
	token_address?: string;
}

export interface RiskManagement {
	stop_loss_percent?: number;
	take_profit_percent?: number;
}

export interface LLMConfig {
	model: string;
	temperature: number;
}

export interface BotConversation {
	id: string;
	bot_id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	created_at: string;
}

export interface Backtest {
	id: string;
	bot_id: string;
	started_at: string;
	ended_at: string | null;
	status: 'running' | 'completed' | 'failed' | 'stopped';
	config: BacktestConfig;
	result: BacktestResult | null;
	progress?: number;
}

export interface BacktestConfig {
	token: string;
	chain: string;
	timeframe: string;
	start_date: string;
	end_date: string;
}

export interface BacktestResult {
	total_return: number;
	win_rate: number;
	total_trades: number;
	buy_signals: number;
	sell_signals: number;
	max_drawdown: number;
	sharpe_ratio: number;
}

export interface Simulation {
	id: string;
	bot_id: string;
	started_at: string;
	status: 'running' | 'stopped';
	config: SimulationConfig;
	signals: Signal[] | null;
}

export interface SimulationConfig {
	token: string;
	interval_seconds: number;
	auto_execute: boolean;
}

export interface Signal {
	id: string;
	bot_id: string;
	run_id: string;
	signal_type: 'buy' | 'sell' | 'hold';
	token: string;
	price: number;
	confidence: number | null;
	reasoning: string | null;
	executed: boolean;
	created_at: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
}

export interface BotChatRequest {
	message: string;
}

export interface BotChatResponse {
	response: string;
	thinking: string | null;
	strategy_config: StrategyConfig | null;
	success: boolean;
}
