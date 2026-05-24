export type ApiError = {
  status: number
  message: string
}

async function request<T>(
  path: string,
  {
    method,
    token,
    body,
    headers,
  }: {
    method: string
    token?: string | null
    body?: unknown
    headers?: Record<string, string>
  },
): Promise<T> {
  const resp = await fetch(path, {
    method,
    headers: {
      ...(body ? { 'content-type': 'application/json' } : {}),
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(headers ?? {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!resp.ok) {
    let message = resp.statusText
    try {
      const data = (await resp.json()) as { detail?: string }
      if (typeof data?.detail === 'string') message = data.detail
    } catch {
      // ignore json parsing errors
    }
    throw { status: resp.status, message } satisfies ApiError
  }

  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

export async function register(email: string, password: string): Promise<void> {
  await request<void>('/api/auth/register', { method: 'POST', body: { email, password } })
}

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)

  const resp = await fetch('/api/auth/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  })

  if (!resp.ok) {
    let message = resp.statusText
    try {
      const data = (await resp.json()) as { detail?: string }
      if (typeof data?.detail === 'string') message = data.detail
    } catch {
      // ignore json parsing errors
    }
    throw { status: resp.status, message } satisfies ApiError
  }

  const data = (await resp.json()) as { access_token: string }
  return data.access_token
}

export type EmailOut = {
  id: number
  subject: string | null
  sender: string | null
  received_at: string | null
  snippet: string | null
  is_unread: boolean
}

export type EmailClassificationOut = {
  id: number
  category: string
  urgency: number
  requires_attention: boolean
  short_summary: string
  suggested_reply: string | null
  confidence: number
}

export type EmailResponse = EmailOut & {
  body: string | null
  classification: EmailClassificationOut | null
}

export async function listEmails(
  token: string,
  { unreadOnly, limit, offset }: { unreadOnly: boolean; limit: number; offset: number },
): Promise<EmailOut[]> {
  const qs = new URLSearchParams()
  qs.set('unread_only', unreadOnly ? 'true' : 'false')
  qs.set('limit', String(limit))
  qs.set('offset', String(offset))
  const data = await request<{ emails: EmailOut[] }>(`/api/emails/?${qs.toString()}`, {
    method: 'GET',
    token,
  })
  return data.emails
}

export async function getEmail(token: string, id: number): Promise<EmailResponse> {
  return await request<EmailResponse>(`/api/emails/${id}`, { method: 'GET', token })
}

export async function classifyEmail(token: string, id: number): Promise<EmailClassificationOut> {
  return await request<EmailClassificationOut>(`/api/emails/${id}/classify`, { method: 'POST', token })
}

export async function syncInbox(token: string): Promise<void> {
  await request<void>('/api/emails/sync', { method: 'POST', token })
}

