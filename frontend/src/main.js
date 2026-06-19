import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

import { Button, setConfig, frappeRequest, resourcesPlugin } from 'frappe-ui'
import Icon from '@/components/ui/Icon.vue'
import { fetchSession } from '@/composables/useSession'

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Icon', Icon)

// Resolve the session before mounting so the router guard can gate the first
// navigation correctly (in-app login vs. dashboard).
fetchSession().then(() => app.mount('#app'))
