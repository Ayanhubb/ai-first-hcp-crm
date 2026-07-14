import { Chip, Paper, Stack, Typography } from '@mui/material'
import type { ProductRef } from '@/shared/types'

type ProductsListProps = {
  products: ProductRef[]
}

export function ProductsList({ products }: ProductsListProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Products
      </Typography>
      {products.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No products suggested yet.
        </Typography>
      ) : (
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {products.map((p) => (
            <Chip key={p.id} label={p.name} size="small" color="primary" variant="outlined" />
          ))}
        </Stack>
      )}
    </Paper>
  )
}
