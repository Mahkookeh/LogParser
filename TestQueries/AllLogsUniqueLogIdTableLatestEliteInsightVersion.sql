SELECT "Boss", "Duration", "Mode", "PlayerId", "Character", "Class", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "LogUrl", "LogId", inhouseplayers, "TotalPlayers", eliteinsightversion FROM (
    SELECT * FROM
        (SELECT "LogUrl", "PlayerId", "Phase", count(unnestedgroup) as InHousePlayers FROM (
                SELECT * FROM (
                    SELECT "LogUrl", "PlayerId", "Boss" , "Phase", unnest("Players") as unnestedPlayer
                    FROM public."Data" NATURAL JOIN public."Logs"
                ) unnestedPlayersTable 
                LEFT JOIN (
                    SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") unnestedGroupsTable 
                ON unnestedPlayer = tempPlayer
                WHERE unnestedGroup = 'Boba'
                ORDER BY "LogUrl" ASC, unnestedPlayersTable."PlayerId" ASC) unnestedPlayersAndGroupsTable
            GROUP BY "LogUrl", unnestedPlayersAndGroupsTable."PlayerId", "Phase") aggregatedInHousePlayersAll
        NATURAL JOIN (
            SELECT "PlayerId" , unnest("Groups") as unnestedGroup FROM public."Players") playerGroupsTable
        WHERE unnestedGroup = 'Boba') aggregatedInHousePlayersAll

NATURAL JOIN (
    
    SELECT max("LogUrl") as LogUrl, "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as EliteInsightVersion FROM 
    public."Data" NATURAL JOIN public."Logs"
    GROUP BY "LogId", "PlayerId", "Phase") organizedEliteInsightVersionTable
    
NATURAL JOIN (
    SELECT * FROM public."Data" NATURAL JOIN public."Logs" 
) allLogsWithDataTable

WHERE "LogUrl" = logurl AND inhouseplayers >=  5
ORDER BY "LogId", "PlayerId", "Phase"