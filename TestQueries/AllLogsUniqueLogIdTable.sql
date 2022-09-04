SELECT distinctEliteInsightVersionFull."LogId", "Boss", "Duration", "Mode", distinctEliteInsightVersionFull."Phase", distinctEliteInsightVersionFull."PlayerId" as "Player Id", "Character", "Class", "TargetDps" as "Target DPS", 
"PercentTargetDps" as "% Target DPS", "PowerDps" as "Power DPS", "CondiDps" as "Condi DPS", "LogUrl" as "Log Url", distinctUniqueEliteInsightVersions."inhouseplayers" as "In-House Players", "TotalPlayers" as "Total Players", "EliteInsightVersion"
FROM (SELECT DISTINCT on ("LogId", "PlayerId", "Phase", "EliteInsightVersion") "LogUrl", "LogId", "PlayerId", "Character", "Class", "Phase", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "Boss", "Mode", "Duration", "TimeStart", "TimeEnd", "TotalPlayers", "EliteInsightVersion", count(unnestedgroup) as InHousePlayers  
FROM (
SELECT "LogUrl", "LogId", "PlayerId", "Character", "Class", "Phase", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "Boss", "Mode", "Duration", "TimeStart", "TimeEnd", "TotalPlayers","EliteInsightVersion", unnest("Players") as unnestedPlayer
FROM public."Data" NATURAL JOIN public."Logs"
) t LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") unnestedPlayers
ON unnestedPlayer = tempPlayer
WHERE unnestedGroup = 'Boba'
GROUP BY "LogUrl", "LogId", "PlayerId", "Character", "Class", "Phase", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "Boss", "Mode", "Duration", "TimeStart", "TimeEnd", "TotalPlayers","EliteInsightVersion"
HAVING count(unnestedgroup) >= 5
ORDER BY "LogId" ASC, "PlayerId" ASC, "Phase" ASC, "EliteInsightVersion" DESC) distinctEliteInsightVersionFull
JOIN  
(SELECT "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as EliteInsightVersion, InHousePlayers
FROM (SELECT DISTINCT on ("LogId", "PlayerId", "Phase", "EliteInsightVersion") "LogUrl", "LogId", "PlayerId", "Phase", "EliteInsightVersion", count(unnestedgroup) as InHousePlayers  
FROM (
SELECT "LogUrl", "LogId", "PlayerId", "Phase", "EliteInsightVersion", unnest("Players") as unnestedPlayer
FROM public."Data" NATURAL JOIN public."Logs"
) t LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") unnestedPlayers
ON unnestedPlayer = tempPlayer
WHERE unnestedGroup = 'Boba'
GROUP BY "LogUrl", "LogId", "PlayerId", "Phase","EliteInsightVersion"
HAVING count(unnestedgroup) >= 5
ORDER BY "LogId" ASC, "PlayerId" ASC, "Phase" ASC, "EliteInsightVersion" DESC) distinctEliteInsightVersions
GROUP BY  "LogId", "PlayerId", "Phase", InHousePlayers) distinctUniqueEliteInsightVersions
ON distinctEliteInsightVersionFull."EliteInsightVersion" = distinctUniqueEliteInsightVersions."eliteinsightversion" and distinctEliteInsightVersionFull."PlayerId" = distinctUniqueEliteInsightVersions."PlayerId"  and distinctEliteInsightVersionFull."LogId" = distinctUniqueEliteInsightVersions."LogId" and distinctEliteInsightVersionFull."Phase" = distinctUniqueEliteInsightVersions."Phase"
ORDER by distinctEliteInsightVersionFull."LogId", distinctEliteInsightVersionFull."PlayerId", distinctEliteInsightVersionFull."Phase"