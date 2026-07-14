import {
  Autocomplete,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from '@mui/material'
import type { Channel, FollowUp, ProductRef, Sentiment } from '@/shared/types'
import { MOCK_PRODUCTS } from '@/mocks/data'

export type InteractionFormValues = {
  visitAt: string
  channel: Channel
  notes: string
  products: ProductRef[]
  topics: string[]
  sentiment: Sentiment | ''
  summary: string
  followUps: FollowUp[]
}

type InteractionFormProps = {
  values: InteractionFormValues
  errors?: Partial<Record<keyof InteractionFormValues, string>>
  onChange: (patch: Partial<InteractionFormValues>) => void
}

export function InteractionForm({ values, errors, onChange }: InteractionFormProps) {
  return (
    <Stack spacing={2.5}>
      <TextField
        label="Visit date & time"
        type="datetime-local"
        value={values.visitAt}
        onChange={(e) => onChange({ visitAt: e.target.value })}
        InputLabelProps={{ shrink: true }}
        error={Boolean(errors?.visitAt)}
        helperText={errors?.visitAt}
        fullWidth
        required
      />

      <FormControl fullWidth required error={Boolean(errors?.channel)}>
        <InputLabel id="channel-label">Channel</InputLabel>
        <Select
          labelId="channel-label"
          label="Channel"
          value={values.channel}
          onChange={(e) => onChange({ channel: e.target.value as Channel })}
        >
          <MenuItem value="in_person">In person</MenuItem>
          <MenuItem value="virtual">Virtual</MenuItem>
          <MenuItem value="phone">Phone</MenuItem>
        </Select>
      </FormControl>

      <TextField
        label="Notes"
        value={values.notes}
        onChange={(e) => onChange({ notes: e.target.value })}
        multiline
        minRows={6}
        fullWidth
        required
        error={Boolean(errors?.notes)}
        helperText={errors?.notes ?? 'Primary visit narrative for AI analysis and CRM record'}
      />

      <Autocomplete
        multiple
        options={MOCK_PRODUCTS}
        getOptionLabel={(o) => o.name}
        value={values.products}
        onChange={(_, products) => onChange({ products })}
        isOptionEqualToValue={(a, b) => a.id === b.id}
        renderInput={(params) => (
          <TextField {...params} label="Products" placeholder="Select products" />
        )}
        renderTags={(tagValue, getTagProps) =>
          tagValue.map((option, index) => (
            <Chip {...getTagProps({ index })} key={option.id} label={option.name} size="small" />
          ))
        }
      />

      <Autocomplete
        multiple
        freeSolo
        options={[]}
        value={values.topics}
        onChange={(_, topics) => onChange({ topics: topics as string[] })}
        renderInput={(params) => (
          <TextField {...params} label="Topics" placeholder="Add topic and press Enter" />
        )}
        renderTags={(tagValue, getTagProps) =>
          tagValue.map((option, index) => (
            <Chip {...getTagProps({ index })} key={option} label={option} size="small" />
          ))
        }
      />

      <FormControl fullWidth>
        <InputLabel id="sentiment-label">Sentiment</InputLabel>
        <Select
          labelId="sentiment-label"
          label="Sentiment"
          value={values.sentiment}
          onChange={(e) =>
            onChange({ sentiment: e.target.value as Sentiment | '' })
          }
        >
          <MenuItem value="">
            <em>Unset</em>
          </MenuItem>
          <MenuItem value="positive">Positive</MenuItem>
          <MenuItem value="neutral">Neutral</MenuItem>
          <MenuItem value="negative">Negative</MenuItem>
        </Select>
      </FormControl>

      <TextField
        label="Summary"
        value={values.summary}
        onChange={(e) => onChange({ summary: e.target.value })}
        multiline
        minRows={3}
        fullWidth
        helperText="Editable after AI Assist"
      />

      <TextField
        label="Follow-ups (one per line)"
        value={values.followUps.map((f) => f.text).join('\n')}
        onChange={(e) =>
          onChange({
            followUps: e.target.value
              .split('\n')
              .map((t) => t.trim())
              .filter(Boolean)
              .map((text, i) => ({
                id: values.followUps[i]?.id ?? `fu-local-${i}`,
                text,
                dueDate: values.followUps[i]?.dueDate,
              })),
          })
        }
        multiline
        minRows={3}
        fullWidth
      />
    </Stack>
  )
}
