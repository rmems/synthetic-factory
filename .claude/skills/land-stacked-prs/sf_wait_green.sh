#!/usr/bin/env bash
# Wait until every check on the given PRs has completed (or 25 min), then print a merge-readiness summary.
R="${SF_REPO:-rmems/synthetic-factory}"; deadline=$((SECONDS+1500))
for n in "$@"; do
  while :; do
    j=$(gh pr view $n --repo $R --json state,mergeable,mergeStateStatus,headRefOid,statusCheckRollup 2>/dev/null) || { sleep 20; continue; }
    state=$(echo "$j" | jq -r .state); pend=$(echo "$j" | jq '[.statusCheckRollup[]? | select(.status!="COMPLETED")] | length'); total=$(echo "$j" | jq '.statusCheckRollup | length')
    if [ "$state" != "OPEN" ] || { [ "$pend" = 0 ] && [ "$total" -ge 9 ]; } || [ $SECONDS -gt $deadline ]; then break; fi
    sleep 45
  done
  fails=$(echo "$j" | jq -r '[.statusCheckRollup[]? | select(.conclusion=="FAILURE") | (.name // .context)] | join(",")')
  unres=$(gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved path comments(first:1){nodes{databaseId author{login} body}}}}}}}' -F o=rmems -F r=synthetic-factory -F n=$n --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false) | "\(.comments.nodes[0].databaseId)|\(.comments.nodes[0].author.login)|\(.path)|\(.comments.nodes[0].body | gsub("<[^>]*>";"") | gsub("\n";" ") | .[0:140])"] | join(" ;; ")')
  echo "READY? #$n state=$state $(echo "$j" | jq -r '"\(.mergeable)/\(.mergeStateStatus)"') head=$(echo "$j" | jq -r '.headRefOid[0:8]') checks=$total pending=$pend fail=[$fails] unresolved=[${unres}]"
done
