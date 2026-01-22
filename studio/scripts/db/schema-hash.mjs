import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

function listSqlFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  const files = entries
    .filter(e => e.isFile())
    .map(e => e.name)
    .filter(name => name.endsWith('.sql'))
    .sort()

  return files.map(name => path.join(dir, name))
}

export function computeMigrationsHash({ migrationsDir }) {
  const files = listSqlFiles(migrationsDir)
  const hash = crypto.createHash('sha256')

  for (const filePath of files) {
    const content = fs.readFileSync(filePath)
    hash.update(path.basename(filePath))
    hash.update('\0')
    hash.update(content)
    hash.update('\0')
  }

  return {
    hash: hash.digest('hex'),
    files: files.map(p => path.basename(p)),
  }
}
