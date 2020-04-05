/** event_attendees_view v1 */
CREATE VIEW event_attendees_view as 
SELECT DISTINCT ON(user_id) user_id, created_at from (
  SELECT user_id, created_at FROM (
    SELECT event_tickets.owner_id AS user_id, event_tickets.created_at AS created_at 
    FROM event_tickets 
    WHERE NOT (
      EXISTS(
        SELECT 1 
        FROM event_ticket_assignments 
        WHERE event_tickets.id = event_ticket_assignments.ticket_id 
        AND event_ticket_assignments.ticket_id = event_tickets.id
      )
    ) AND event_tickets.event_id='2d5026ff-fe2b-4df8-a666-9ac748a05bcf' ORDER BY created_at ASC
  ) tbl 
  UNION 
  SELECT event_ticket_assignments.assigned_to_user_id AS user_id, event_ticket_assignments.created_at AS created_at 
  FROM event_ticket_assignments WHERE ticket_id IN (SELECT id FROM event_tickets WHERE event_id='2d5026ff-fe2b-4df8-a666-9ac748a05bcf')
  ORDER BY created_at ASC
) tbl 

/** event_attendees_view v2 */
DROP VIEW if exists event_attendees_view;
CREATE VIEW event_attendees_view as 
SELECT DISTINCT ON(user_id, event_id) user_id, created_at, event_id from (
  SELECT user_id, created_at, event_id FROM (
    SELECT event_tickets.owner_id AS user_id, event_tickets.created_at AS created_at, event_id
    FROM event_tickets 
    WHERE NOT (
      EXISTS(
        SELECT 1 
        FROM event_ticket_assignments 
        WHERE event_tickets.id = event_ticket_assignments.ticket_id 
        AND event_ticket_assignments.ticket_id = event_tickets.id
      )
    )  ORDER BY created_at ASC
  ) tbl 
  UNION 
  SELECT event_ticket_assignments.assigned_to_user_id AS user_id, event_ticket_assignments.created_at AS created_at, event_id
  FROM event_ticket_assignments
  ORDER BY created_at ASC
) tbl




/** Old Query */
SELECT * FROM users WHERE id IN (
SELECT DISTINCT ON(user_id) user_id from (
  SELECT user_id, created_at FROM (
    SELECT event_tickets.owner_id AS user_id, event_tickets.created_at AS created_at 
    FROM event_tickets 
    WHERE NOT (
      EXISTS(
        SELECT 1 
        FROM event_ticket_assignments 
        WHERE event_tickets.id = event_ticket_assignments.ticket_id 
        AND event_ticket_assignments.ticket_id = event_tickets.id
      )
    ) AND event_tickets.event_id=:event_id ORDER BY created_at ASC
  ) tbl 
  UNION 
  SELECT event_ticket_assignments.assigned_to_user_id AS user_id, event_ticket_assignments.created_at AS created_at 
  FROM event_ticket_assignments WHERE ticket_id IN (SELECT id FROM event_tickets WHERE event_id=:event_id)
  ORDER BY created_at ASC
) tbl 
WHERE CASE WHEN COALESCE(:cursor_after,0)!=0 THEN extract('epoch' FROM created_at) > :cursor_after ELSE TRUE END
AND CASE WHEN  COALESCE(:cursor_before,0)!=0 THEN extract('epoch' FROM created_at) < :cursor_before ELSE TRUE END
) ORDER BY created_at ASC LIMIT :limit 