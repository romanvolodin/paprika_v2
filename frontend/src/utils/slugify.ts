/**
 * Transliterates Cyrillic (and any other text) into a URL-friendly slug:
 * lowercases, maps Cyrillic letters to their Latin equivalents, then
 * collapses everything that isn't a letter/digit into single hyphens.
 *
 * This is a client-side convenience only - the backend's `Company.slug`
 * field doesn't require Latin characters (it accepts any slug via
 * Django's `slugify(allow_unicode=True)`), but a Latin, human-readable
 * slug is nicer to have in URLs than raw Cyrillic.
 */
const CYRILLIC_TO_LATIN: Record<string, string> = {
  а: 'a',
  б: 'b',
  в: 'v',
  г: 'g',
  д: 'd',
  е: 'e',
  ё: 'e',
  ж: 'zh',
  з: 'z',
  и: 'i',
  й: 'y',
  к: 'k',
  л: 'l',
  м: 'm',
  н: 'n',
  о: 'o',
  п: 'p',
  р: 'r',
  с: 's',
  т: 't',
  у: 'u',
  ф: 'f',
  х: 'kh',
  ц: 'ts',
  ч: 'ch',
  ш: 'sh',
  щ: 'shch',
  ъ: '',
  ы: 'y',
  ь: '',
  э: 'e',
  ю: 'yu',
  я: 'ya',
}

export function slugify(value: string): string {
  const transliterated = value
    .toLowerCase()
    .split('')
    .map((char) => CYRILLIC_TO_LATIN[char] ?? char)
    .join('')

  return transliterated
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
