import { Button, Stack, TextField } from '@mui/material'
import { useState } from 'react'

type EditAssistControlsProps = {
  disabled?: boolean
  loading?: boolean
  onApply: (instruction: string) => void
}

export function EditAssistControls({
  disabled,
  loading,
  onApply,
}: EditAssistControlsProps) {
  const [instruction, setInstruction] = useState('')

  return (
    <Stack spacing={1.5}>
      <TextField
        label="Edit instruction"
        placeholder="e.g. Make the summary shorter and emphasize sample request"
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        multiline
        minRows={2}
        fullWidth
        disabled={disabled || loading}
      />
      <Button
        variant="outlined"
        disabled={disabled || loading || !instruction.trim()}
        onClick={() => {
          onApply(instruction.trim())
          setInstruction('')
        }}
      >
        {loading ? 'Applying…' : 'Apply edit'}
      </Button>
    </Stack>
  )
}
