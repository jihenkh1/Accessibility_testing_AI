type Props = {
  issue: Record<string, any>
}

const badgeColor = (p: string) =>
  p === 'critical' || p === 'high' ? 'bg-red-600' : p === 'medium' ? 'bg-yellow-500' : 'bg-green-600'

export default function IssueCard({ issue }: Props) {
  return (
    <div className="rounded border bg-white p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className={`text-xs text-white px-2 py-1 rounded ${badgeColor(issue.priority)}`}>{issue.priority}</span>
        <div className="font-semibold flex-1">{issue.rule_id}</div>
        {issue.source && <span className="text-xs bg-gray-100 px-2 py-1 rounded">{issue.source}</span>}
      </div>
      {issue.user_impact && <div className="text-sm">{issue.user_impact}</div>}
      {issue.fix_suggestion && <div className="text-sm text-gray-700">{issue.fix_suggestion}</div>}
      <div className="text-xs flex items-center gap-3">
        <span>Effort: {issue.effort_minutes}m</span>
        {issue.selector && <span className="truncate">Selector: {issue.selector}</span>}
      </div>
      {issue.wcag_refs && issue.wcag_refs.length > 0 && (
        <div className="text-xs text-gray-700">WCAG: {issue.wcag_refs.join(', ')}</div>
      )}
    </div>
  )}

