# Activity Log: {{case_id}}

Append-only historical record of significant state transitions and workflow re-entries.

---

## {{timestamp}}

**Event**: Case created  
**Lifecycle**: new → collecting  
**Trigger**: User provided initial issue materials  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Evidence collection complete  
**Lifecycle**: collecting → collected  
**Trigger**: Curated evidence set is sufficient for downstream work  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Handoff started  
**Lifecycle**: collected → handoff_in_progress  
**Trigger**: {{trigger}}  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Handoff ready  
**Lifecycle**: handoff_in_progress → handoff_ready  
**Trigger**: All handoff artifacts complete  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Resolution started  
**Lifecycle**: handoff_ready → resolve_in_progress  
**Trigger**: {{trigger}}  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Resolution complete  
**Lifecycle**: resolve_in_progress → resolved_verified  
**Trigger**: Fix implemented and verified  
**Details**: {{details}}

---

## {{timestamp}}

**Event**: Case closed  
**Lifecycle**: resolved_verified → closed  
**Trigger**: No further action needed  
**Details**: {{details}}

---

## Reopening Template

## {{timestamp}}

**Event**: Case reopened  
**Lifecycle**: closed → {{new_state}}  
**Trigger**: {{trigger}}  
**Reason**: {{reason}}  
**Details**: {{details}}

---

## Recollect Template

## {{timestamp}}

**Event**: Recollect triggered  
**Lifecycle**: {{current_state}} → collecting  
**Trigger**: {{trigger}}  
**Reason**: {{reason}}  
**New source**: {{new_source}}  
**Details**: {{details}}

---

## Blocked Template

## {{timestamp}}

**Event**: Case blocked  
**Lifecycle**: {{current_state}} → blocked  
**Trigger**: {{trigger}}  
**Blocker**: {{blocker}}  
**Details**: {{details}}
