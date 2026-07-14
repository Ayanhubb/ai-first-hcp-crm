import { Box, Chip, Stack, Typography } from '@mui/material'
import type { Hcp } from '@/shared/types'

type HcpIdentityHeaderProps = {
  hcp: Hcp
}

export function HcpIdentityHeader({ hcp }: HcpIdentityHeaderProps) {
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="h5" component="h2">
        {hcp.name}
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
        <Chip size="small" label={hcp.specialty} />
        <Chip size="small" variant="outlined" label={hcp.institution} />
        <Chip size="small" variant="outlined" label={hcp.city} />
      </Stack>
    </Box>
  )
}
