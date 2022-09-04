SELECT "LogId", "Boss", "Duration", "Mode", "Phase", "PlayerId", "Character", "Class", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "LogUrl", "inhouseplayers", "TotalPlayers", "EliteInsightVersion" FROM(
        SELECT * FROM 
        (SELECT * FROM (SELECT "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as "EliteInsightVersion"  FROM public."Data" NATURAL JOIN public."Logs"
        Group by "LogId", "PlayerId", "Phase") x LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") y
        ON "PlayerId" = tempPlayer
        WHERE unnestedGroup = 'Boba') t NATURAL JOIN (SELECT * FROM public."Data" NATURAL JOIN public."Logs") m ORDER BY "TargetDps" DESC) FilteredData
        NATURAL JOIN 
        (SELECT "LogUrl", "PlayerId", "Phase", count(unnestedgroup) as InHousePlayers FROM (
        SELECT * FROM (
        SELECT "LogUrl", "PlayerId", "Boss" , "Phase", unnest("Players") as unnestedPlayer
        FROM public."Data" NATURAL JOIN public."Logs" where "Boss" = 'Sabetha the Saboteur'
        ) t LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") j 
        ON unnestedPlayer = tempPlayer
        WHERE unnestedGroup = 'Boba'
        ORDER BY "LogUrl" ASC, t."PlayerId" ASC) q
        GROUP BY "LogUrl", q."PlayerId", "Phase") InHouseData where inhouseplayers >= 5