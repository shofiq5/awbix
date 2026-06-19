import { reactive } from 'vue'

// Shared, app-wide session state. Populated on bootstrap (main.js) and kept in
// sync by login()/logout(). Components read `session.isLoggedIn`, `session.user`,
// etc. reactively; the router guard reads it to gate protected routes.
export const session = reactive({
  user: null,
  fullName: '',
  isLoggedIn: false,
})

function setGuest() {
  session.user = null
  session.fullName = ''
  session.isLoggedIn = false
  window.frappe = window.frappe || {}
  window.frappe.session = { user: 'Guest', user_fullname: 'Guest' }
}

function setUser({ user, user_fullname, csrf_token }) {
  session.user = user
  session.fullName = user_fullname || user
  session.isLoggedIn = true

  window.frappe = window.frappe || {}
  window.frappe.session = { user, user_fullname: session.fullName }
  if (csrf_token) {
    window.csrf_token = csrf_token
    window.frappe.csrf_token = csrf_token
  }
}

// Resolve the current session. Honors a real Frappe-injected session first
// (production / Frappe-served mode), otherwise asks the backend.
export async function fetchSession() {
  const injected = window.frappe?.session?.user
  if (injected && injected !== 'Guest') {
    setUser({ user: injected, user_fullname: window.frappe.session.user_fullname })
    return session
  }

  try {
    const res = await fetch('/api/method/awbix.frontend_api.get_session_info', {
      headers: { Accept: 'application/json' },
    })
    if (res.ok) {
      const { message } = await res.json()
      if (message && message.user && message.user !== 'Guest') {
        setUser(message)
        return session
      }
    }
  } catch {
    // Network error — fall through to guest; the router guard redirects to login.
  }

  setGuest()
  return session
}

// Authenticate against Frappe's login endpoint. Throws with a readable message
// on failure; refreshes the session (user + CSRF token) on success.
export async function login(email, password) {
  const res = await fetch('/api/method/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Accept: 'application/json',
    },
    body: new URLSearchParams({ usr: email, pwd: password }),
  })

  if (!res.ok) {
    let message = 'Invalid email or password.'
    try {
      const j = await res.json()
      message = j.message || message
    } catch {}
    throw new Error(message)
  }

  await fetchSession()
  return session
}

// End the Frappe session, then clear client state regardless of outcome.
export async function logout() {
  try {
    await fetch('/api/method/logout', {
      method: 'POST',
      headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' },
    })
  } catch {
    // ignore — clear local state regardless
  }
  setGuest()
}
