import { useMemo, useState } from 'react'

import {
  getTraceChildren,
  isPlainObject,
  traceNodeFacts,
  traceNodeTitle,
  type TraceNode,
  type TraceSpan,
} from './orderTraceDebug'
import { TraceNodeDetailsView } from './TraceNodeDetailsView'

type OpenNodes = Record<string, boolean>

type Props = {
  root: TraceSpan
  resolveArtifactRef?: (ref: string) => { value: string; contentType?: string } | null
}

function nodeKey(path: number[], node: TraceNode): string {
  const name = typeof node.name === 'string' ? node.name : ''
  const type = typeof node.type === 'string' ? node.type : ''
  return `${path.join('.')}:${type}:${name}`
}

function hasDetails(node: TraceNode): boolean {
  if (!isPlainObject(node)) return false
  if (isPlainObject(node.error) && Object.keys(node.error).length) return true

  const artifacts = (node as Record<string, unknown>).artifacts
  if (Array.isArray(artifacts) && artifacts.some(isPlainObject)) return true

  return false
}

export function TraceTreeView(props: Props) {
  const { root, resolveArtifactRef } = props
  const [openNodes, setOpenNodes] = useState<OpenNodes>(() => ({ '': true }))

  const nodes = useMemo(() => getTraceChildren(root as unknown as TraceNode), [root])

  const renderNode = (node: TraceNode, depth: number, path: number[]) => {
    const key = nodeKey(path, node)
    const open = !!openNodes[key]

    const children = getTraceChildren(node)
    const title = traceNodeTitle(node)
    const facts = traceNodeFacts(node)
    const subtitle = facts.length ? facts.join(' · ') : null

    const canExpand = children.length > 0 || hasDetails(node)

    return (
      <div key={key} className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg)]">
        <button
          type="button"
          onClick={() => {
            if (!canExpand) return
            setOpenNodes(prev => ({ ...prev, [key]: !prev[key] }))
          }}
          className="w-full text-left px-2 py-1 flex items-start gap-2"
          style={{ paddingLeft: 8 + depth * 14 }}
        >
          <span className="shrink-0 font-mono text-xs mt-[1px]">{canExpand ? (open ? '▼' : '▶') : '·'}</span>
          <span className="min-w-0">
            <div className="font-mono text-xs whitespace-pre-wrap break-all">{title}</div>
            {subtitle ? (
              <div className="font-mono text-xs whitespace-pre-wrap break-all text-[color:var(--text-secondary)]">
                {subtitle}
              </div>
            ) : null}
          </span>
        </button>

        {open && hasDetails(node) ? (
          <div className="px-2 pb-2" style={{ paddingLeft: 22 + depth * 14 }}>
            <TraceNodeDetailsView node={node} resolveArtifactRef={resolveArtifactRef} />
          </div>
        ) : null}

        {open && children.length ? (
          <div className="px-2 pb-2 space-y-1">
            {children.map((child, idx) => renderNode(child, depth + 1, [...path, idx]))}
          </div>
        ) : null}
      </div>
    )
  }

  if (!nodes.length) {
    return <div className="text-sm text-[color:var(--text-secondary)]">No trace nodes.</div>
  }

  return <div className="space-y-2">{nodes.map((n, idx) => renderNode(n, 0, [idx]))}</div>
}
