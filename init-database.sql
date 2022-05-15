CREATE TABLE counters (ID int PRIMARY KEY, countvalue int);
INSERT INTO counters (ID, countvalue) VALUES (1, 0);

SELECT * FROM counters;

UPDATE counters SET countvalue = countvalue + 1 WHERE ID=1;

SELECT countvalue FROM counters WHERE ID=1;
