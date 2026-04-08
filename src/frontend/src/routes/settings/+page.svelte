<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, userStore, logout } from '$lib/stores';
	import { api } from '$lib/api';

	let email = $state('');
	let currentPassword = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let isUpdating = $state(false);
	let updateSuccess = $state('');
	let updateError = $state('');

	onMount(async () => {
		if (!$isAuthenticated && !$isLoading) {
			goto('/login');
			return;
		}
		if ($userStore) {
			email = $userStore.email;
		}
	});

	async function updateEmail() {
		updateSuccess = '';
		updateError = '';
		isUpdating = true;
		try {
			await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/settings`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.getItem('token')}`
				},
				body: JSON.stringify({ email })
			});
			updateSuccess = 'Email updated successfully';
		} catch (e) {
			updateError = e instanceof Error ? e.message : 'Failed to update email';
		} finally {
			isUpdating = false;
		}
	}

	async function updatePassword() {
		updateSuccess = '';
		updateError = '';

		if (newPassword !== confirmPassword) {
			updateError = 'Passwords do not match';
			return;
		}

		if (newPassword.length < 6) {
			updateError = 'Password must be at least 6 characters';
			return;
		}

		isUpdating = true;
		try {
			await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/settings`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.getItem('token')}`
				},
				body: JSON.stringify({ password: newPassword, current_password: currentPassword })
			});
			updateSuccess = 'Password updated successfully';
			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
		} catch (e) {
			updateError = e instanceof Error ? e.message : 'Failed to update password';
		} finally {
			isUpdating = false;
		}
	}

	function handleLogout() {
		logout();
		goto('/');
	}
</script>

<svelte:head>
	<title>Settings - Randebu</title>
</svelte:head>

<main>
	<header>
		<div class="header-left">
			<a href="/dashboard" class="back-link">← Dashboard</a>
			<h1>Settings</h1>
		</div>
	</header>

	<div class="content">
		<section class="settings-section">
			<h2>Profile</h2>
			
			{#if updateSuccess}
				<div class="success">{updateSuccess}</div>
			{/if}
			
			{#if updateError}
				<div class="error">{updateError}</div>
			{/if}

			<form onsubmit={(e) => { e.preventDefault(); updateEmail(); }}>
				<div class="field">
					<label for="email">Email</label>
					<input type="email" id="email" bind:value={email} required />
				</div>
				<button type="submit" disabled={isUpdating}>
					{isUpdating ? 'Updating...' : 'Update Email'}
				</button>
			</form>
		</section>

		<section class="settings-section">
			<h2>Change Password</h2>
			
			<form onsubmit={(e) => { e.preventDefault(); updatePassword(); }}>
				<div class="field">
					<label for="currentPassword">Current Password</label>
					<input type="password" id="currentPassword" bind:value={currentPassword} required />
				</div>
				<div class="field">
					<label for="newPassword">New Password</label>
					<input type="password" id="newPassword" bind:value={newPassword} required minlength="6" />
				</div>
				<div class="field">
					<label for="confirmPassword">Confirm New Password</label>
					<input type="password" id="confirmPassword" bind:value={confirmPassword} required />
				</div>
				<button type="submit" disabled={isUpdating}>
					{isUpdating ? 'Updating...' : 'Update Password'}
				</button>
			</form>
		</section>

		<section class="settings-section danger-section">
			<h2>Account</h2>
			<button onclick={handleLogout} class="btn btn-danger">
				Logout
			</button>
		</section>
	</div>
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: #0f0f0f;
		color: #fff;
	}

	main {
		min-height: 100vh;
		max-width: 600px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		margin-bottom: 2rem;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.back-link {
		color: #667eea;
		text-decoration: none;
		font-size: 0.9rem;
	}

	h1 {
		margin: 0;
		font-size: 1.75rem;
	}

	.content {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	section {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
	}

	h2 {
		font-size: 1.1rem;
		margin: 0 0 1rem;
	}

	.success {
		background: rgba(34, 197, 94, 0.2);
		border: 1px solid #22c55e;
		color: #86efac;
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.error {
		background: rgba(239, 68, 68, 0.2);
		border: 1px solid #ef4444;
		color: #fca5a5;
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.field {
		margin-bottom: 1rem;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		color: #ccc;
		font-size: 0.9rem;
	}

	input {
		width: 100%;
		padding: 0.75rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		box-sizing: border-box;
	}

	input:focus {
		outline: none;
		border-color: #667eea;
	}

	button {
		width: 100%;
		padding: 0.875rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: transform 0.2s;
	}

	button:hover:not(:disabled) {
		transform: translateY(-2px);
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.danger-section button {
		background: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
		border: 1px solid rgba(239, 68, 68, 0.4);
	}
</style>
