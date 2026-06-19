import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

import { Button, setConfig, frappeRequest, resourcesPlugin } from 'frappe-ui'
import Icon from '@/components/ui/Icon.vue'

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Icon', Icon)

async function initSession() {
	// Skip if Frappe already injected a real session (production / Frappe-served mode)
	if (window.frappe?.session?.user && window.frappe.session.user !== 'Guest') {
		return
	}
	try {
		const res = await fetch('/api/method/awbix.frontend_api.get_session_info')
		if (!res.ok) return
		const { message } = await res.json()
		if (!message || message.user === 'Guest') return

		window.frappe = window.frappe || {}
		window.frappe.session = {
			user: message.user,
			user_fullname: message.user_fullname,
		}
		// Make the real CSRF token available to frappeRequest
		window.csrf_token = message.csrf_token
		window.frappe.csrf_token = message.csrf_token
	} catch (_) {
		// Network error — router guard will handle the redirect to login
	}
}

initSession().then(() => app.mount('#app'))
