import type { ComponentProps } from "react"

import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
} from "@/shared/ui/input-group"

/** Un monto en dólares. Va como texto (`1.250,50`): lo interpreta y valida la API. */
export function InputUSD({
  className,
  ...props
}: ComponentProps<typeof InputGroupInput>) {
  return (
    <InputGroup className={className}>
      <InputGroupAddon>
        <InputGroupText>US$</InputGroupText>
      </InputGroupAddon>
      <InputGroupInput
        inputMode="decimal"
        autoComplete="off"
        placeholder="1.250"
        className="tabular-nums"
        {...props}
      />
    </InputGroup>
  )
}
