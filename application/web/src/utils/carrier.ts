const PALETTE: { bg: string; fg: string }[] = [
  { bg: '#E6EBFB', fg: '#1F3FD6' },
  { bg: '#E1F2EA', fg: '#15795A' },
  { bg: '#FAEEDA', fg: '#8A5208' },
  { bg: '#F1E7FA', fg: '#6B2BB0' },
  { bg: '#FBE5E7', fg: '#A8202C' },
  { bg: '#E3F2F7', fg: '#0F6B85' },
]

export function carrierColors(code: string): { bg: string; fg: string } {
  let h = 0
  for (const ch of code) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return PALETTE[h % PALETTE.length] ?? { bg: '#E6EBFB', fg: '#1F3FD6' }
}
