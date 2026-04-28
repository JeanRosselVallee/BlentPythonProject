-- SQLite
select * from utilisateur;
select * from produit; --where id='42';
select * from commande;
select * from ligne_commande;

-- Remove new records created during tests
delete from utilisateur where id > 12;
delete from commande where id > 10;
delete from ligne_commande where commande_id > 10;

-- Give admin rights to user admin
update utilisateur set role = "admin" where nom = "admin";


insert into commande (utilisateur_id, date_commande, adresse_livraison, statut) values (12, '2026-04-24 10:14:08.801398', NULL, 'en_attente')

DROP table utilisateur;
DROP TABLE produit;
drop table commande;
drop table ligne_commande;


SELECT 
            lc.commande_id, 
            p.nom, 
            lc.quantite, 
            lc.prix_unitaire
        FROM ligne_commande lc
     JOIN produit p ON lc.produit_id = p.id 
     JOIN commande c ON lc.commande_id = c.id 
     WHERE lc.commande_id = 11 AND c.utilisateur_id = 11;