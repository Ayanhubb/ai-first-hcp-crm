import { FormControl, InputLabel, MenuItem, Select, Stack } from '@mui/material'

type FilterRowProps = {
  specialty: string
  city: string
  specialties: string[]
  cities: string[]
  onSpecialtyChange: (value: string) => void
  onCityChange: (value: string) => void
}

export function FilterRow({
  specialty,
  city,
  specialties,
  cities,
  onSpecialtyChange,
  onCityChange,
}: FilterRowProps) {
  return (
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
      <FormControl fullWidth size="small">
        <InputLabel id="specialty-filter-label">Specialty</InputLabel>
        <Select
          labelId="specialty-filter-label"
          label="Specialty"
          value={specialty}
          onChange={(e) => onSpecialtyChange(e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          {specialties.map((s) => (
            <MenuItem key={s} value={s}>
              {s}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl fullWidth size="small">
        <InputLabel id="city-filter-label">City</InputLabel>
        <Select
          labelId="city-filter-label"
          label="City"
          value={city}
          onChange={(e) => onCityChange(e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          {cities.map((c) => (
            <MenuItem key={c} value={c}>
              {c}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  )
}
