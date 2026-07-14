import { Alert, Button, Stack, TextField, Typography } from '@mui/material'
import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { login } from '@/features/auth/authSlice'
import { ROUTES } from '@/shared/constants/routes'

export function LoginPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const { status, error } = useAppSelector((s) => s.auth)
  const [email, setEmail] = useState('priya.sharma@example.com')
  const [password, setPassword] = useState('demo')

  const from =
    (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ||
    ROUTES.dashboard

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const result = await dispatch(login({ email, password }))
    if (login.fulfilled.match(result)) {
      navigate(from, { replace: true })
    }
  }

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
      <Typography variant="h5" component="h1">
        Sign in
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Demo mode — no backend. Use any email and a password with 4+ characters.
      </Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <TextField
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        fullWidth
        autoComplete="username"
      />
      <TextField
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        fullWidth
        autoComplete="current-password"
      />
      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={status === 'loading'}
      >
        {status === 'loading' ? 'Signing in…' : 'Sign in'}
      </Button>
    </Stack>
  )
}
