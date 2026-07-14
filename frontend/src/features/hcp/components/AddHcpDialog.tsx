import { useState } from 'react'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material'
import { hcpApi, type CreateHcpPayload } from '@/services/hcpApi'
import { ApiError } from '@/services/http'
import type { Hcp } from '@/shared/types'

type AddHcpDialogProps = {
  open: boolean
  onClose: () => void
  onCreated: (hcp: Hcp) => void
}

const emptyForm: CreateHcpPayload = {
  firstName: '',
  lastName: '',
  specialty: '',
  institution: '',
  city: '',
  state: '',
  country: '',
  email: '',
  phone: '',
}

export function AddHcpDialog({ open, onClose, onCreated }: AddHcpDialogProps) {
  const [form, setForm] = useState<CreateHcpPayload>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const patch = (key: keyof CreateHcpPayload, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleClose = () => {
    if (saving) return
    setForm(emptyForm)
    setError(null)
    onClose()
  }

  const handleSave = async () => {
    if (!form.firstName.trim() || !form.lastName.trim() || !form.specialty.trim()) {
      setError('First name, last name, and specialty are required.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const created = await hcpApi.create(form)
      setForm(emptyForm)
      onCreated(created)
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create HCP')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Add doctor / HCP</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="First name"
              value={form.firstName}
              onChange={(e) => patch('firstName', e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Last name"
              value={form.lastName}
              onChange={(e) => patch('lastName', e.target.value)}
              required
              fullWidth
            />
          </Stack>
          <TextField
            label="Specialty"
            value={form.specialty}
            onChange={(e) => patch('specialty', e.target.value)}
            required
            fullWidth
            placeholder="e.g. Cardiology"
          />
          <TextField
            label="Institution"
            value={form.institution}
            onChange={(e) => patch('institution', e.target.value)}
            fullWidth
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="City"
              value={form.city}
              onChange={(e) => patch('city', e.target.value)}
              fullWidth
            />
            <TextField
              label="State"
              value={form.state}
              onChange={(e) => patch('state', e.target.value)}
              fullWidth
            />
          </Stack>
          <TextField
            label="Country"
            value={form.country}
            onChange={(e) => patch('country', e.target.value)}
            fullWidth
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Email"
              value={form.email}
              onChange={(e) => patch('email', e.target.value)}
              fullWidth
            />
            <TextField
              label="Phone"
              value={form.phone}
              onChange={(e) => patch('phone', e.target.value)}
              fullWidth
            />
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button type="button" onClick={handleClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          type="button"
          variant="contained"
          onClick={() => void handleSave()}
          disabled={saving}
        >
          {saving ? 'Saving…' : 'Create HCP'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
