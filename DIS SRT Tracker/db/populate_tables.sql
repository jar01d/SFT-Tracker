-- Insert values into achievement table
INSERT INTO achievement (name) VALUES 
('Gold'),
('Silver'),
('Pass');

-- Insert values into instructor table
INSERT INTO instructor (name) VALUES 
('Xing Mei');

-- Insert values into activity table
INSERT INTO activity (name) VALUES 
('Run - Wingline'),
('Run - Running Path'),
('Gym - Wingline'),
('Basketball - Wingline')

INSERT into status (name) VALUES ('Pending'),('Ongoing'),('Completed')


SELECT 
	cadet.name AS cadet_name,
	activity.name AS activity_name,
	sft_info.datetime_in,
	sft_info.datetime_out,
	created_on,
	status.name AS status_name
FROM 
	sft_info
JOIN cadet ON sft_info.cadet_id = cadet.cadet_id
JOIN activity ON sft_info.activity_id = activity.activity_id
JOIN status ON sft_info.status_id = status.status_id
WHERE cadet.telegram_id = '641584480'


SELECT 
	status.status_id
FROM 
	sft_info
JOIN cadet ON sft_info.cadet_id = cadet.cadet_id
JOIN status ON sft_info.status_id = status.status_id
WHERE cadet.telegram_id = '641584480'


select * from status
select * from srt_info;
select * from activity
select * from status
SELECT * from cadet;
select * from 'group'

INSERT INTO 'group' (tele_id, name) VALUES 
(NULL, "No Group")

delete from 'group'


select * from cadet_group

DELETE from sft_info

DELETE FROM sft_info
WHERE cadet_id = 1
AND rowid NOT IN (
	SELECT rowid
	FROM sft_info
	WHERE cadet_id = 1
	ORDER BY created_on DESC
	LIMIT 1
)

SELECT rowid
FROM sft_info
WHERE cadet_id = 1
ORDER BY created_on DESC
LIMIT 1

select * from activity

update activity set name = 'Basketball - Basketball Court' where activity_id = 4
	