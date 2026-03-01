export async function runWithConcurrency<TItem>(
  items: TItem[],
  limit: number,
  worker: (item: TItem) => Promise<void>
): Promise<void> {
  if (limit <= 0) throw new Error('Concurrency limit must be > 0')

  let index = 0

  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (true) {
      const currentIndex = index
      index += 1
      if (currentIndex >= items.length) return
      await worker(items[currentIndex])
    }
  })

  await Promise.all(runners)
}
