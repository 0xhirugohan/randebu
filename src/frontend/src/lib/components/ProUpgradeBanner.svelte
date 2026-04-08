<script lang="ts">
	interface Props {
		feature?: string;
		dismissible?: boolean;
		onDismiss?: () => void;
	}

	let { feature, dismissible = true, onDismiss }: Props = $props();
</script>

<div class="pro-upgrade-banner">
	<div class="banner-content">
		<div class="banner-icon">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
			</svg>
		</div>
		<div class="banner-text">
			<strong>Upgrade to Pro</strong>
			{#if feature}
				<p>{feature}</p>
			{:else}
				<p>Unlock advanced features and unlimited bots</p>
			{/if}
		</div>
		<a href="/settings" class="upgrade-btn">Upgrade Now</a>
	</div>
	{#if dismissible && onDismiss}
		<button class="dismiss-btn" onclick={onDismiss} aria-label="Dismiss">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="18" y1="6" x2="6" y2="18"></line>
				<line x1="6" y1="6" x2="18" y2="18"></line>
			</svg>
		</button>
	{/if}
</div>

<style>
	.pro-upgrade-banner {
		position: relative;
		display: flex;
		align-items: center;
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
		border: 1px solid rgba(102, 126, 234, 0.3);
		border-radius: 12px;
		padding: 1rem 1.5rem;
		margin: 1rem 0;
	}

	.banner-content {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex: 1;
	}

	.banner-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: rgba(102, 126, 234, 0.2);
		border-radius: 8px;
		color: #667eea;
	}

	.banner-text {
		flex: 1;
	}

	.banner-text strong {
		display: block;
		color: #fff;
		font-size: 1rem;
		margin-bottom: 0.25rem;
	}

	.banner-text p {
		margin: 0;
		font-size: 0.85rem;
		color: #aaa;
	}

	.upgrade-btn {
		padding: 0.5rem 1rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 500;
		font-size: 0.9rem;
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.upgrade-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.dismiss-btn {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		transition: background 0.2s, color 0.2s;
	}

	.dismiss-btn:hover {
		background: rgba(255, 255, 255, 0.1);
		color: #fff;
	}
</style>