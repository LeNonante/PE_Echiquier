# Documentation M.A.E.L.

![L'échiquier M.A.E.L.](images/echiquier.jpg)

M.A.E.L. est un échiquier physique connecté à [Lichess](https://lichess.org). Il permet de jouer de vraies parties en ligne (contre l'IA ou contre d'autres joueurs) en déplaçant les pièces sur un plateau réel, tout en se pilotant depuis cette interface web.

## Sommaire

1. [Premier démarrage](#premier-demarrage)
2. [Connexion à Lichess](#connexion-a-lichess)
3. [Jouer une partie](#jouer-une-partie)
4. [Mode démonstration](#mode-demonstration)
5. [Dépannage](#depannage)

## Premier démarrage

### Connexion au Wi-Fi

???

### Accéder à l'interface

Depuis un ordinateur, une tablette ou un téléphone connecté au **même réseau**, ouvrez un navigateur et rendez-vous sur [mael.local](mael.local). La page d'accueil s'affiche.

## Connexion à Lichess

L'échiquier communique avec Lichess grâce à un **token d'API** personnel.

### Obtenir un token

1. Connectez-vous à votre compte sur [lichess.org](https://lichess.org).
2. Ouvrez la page [Jetons d'accès personnels](https://lichess.org/account/oauth/token) (Préférences → API access tokens).
3. Créez un nouveau jeton en cochant au minimum les autorisations :
    - `challenge:read`
    - `challenge:write`
    - `challenge:bulk`
    - `board:play`
    - `engine:read`
    - `engine:write`
4. Copiez le jeton généré (il ne sera plus affiché ensuite).

### Enregistrer le token dans l'échiquier

Cliquez sur l'icône **paramètres** en haut à droite de l'accueil, collez le jeton puis enregistrez. Si le jeton est valide, le badge **Compte Lichess** de l'accueil affiche votre pseudo avec un voyant vert. Un voyant rouge indique que l'échiquier n'est pas connecté.

Le bouton **Se déconnecter** de la même page efface le jeton enregistré.

## Jouer une partie

### Défier l'IA

Choisissez :

| Paramètre | Valeurs possibles |
|---|---|
| Niveau de l'IA | de 1 (débutant) à 8 (très fort) |
| Votre couleur | Blanc, Noir ou Aléatoire |
| Limite de temps | 15, 30, 45 s ou un multiple de 60 s (ou aucune limite) |
| Incrément | secondes ajoutées après chaque coup (ou aucun incrément) |

> **Bon à savoir :** Lichess impose une limite et un incrément ensemble. Sans limite de temps, la partie se joue donc sans pendule.

### Défier un joueur en ligne

Indiquez le **pseudo Lichess** de votre adversaire, puis la couleur et le contrôle du temps, avec les mêmes règles que pour l'IA. Le défi lui est envoyé : la partie commence dès qu'il l'accepte. Les défis sont toujours **non classés**.

### Rejoindre une partie

Cette page liste les parties en cours sur votre compte Lichess. Sélectionnez-en une pour la reprendre sur le plateau physique.

### Suivi de la partie

Pendant la partie, la page de suivi se met à jour en temps réel : coups joués, temps restant de chaque joueur et fin de partie.

## Mode démonstration

Le mode démonstration rejoue seul des parties célèbres de l'histoire des échecs, sans connexion à Lichess. Il est idéal pour utiliser l'échiquier comme objet de décoration.

Depuis la page **Lancer une démonstration**, choisissez une partie puis cliquez sur **Lancer**. Ce mode est également accessible directement depuis le plateau physique. Pour cela :
- ????

## Dépannage

**Le badge affiche « Déconnecté ».**
Le jeton est absent ou invalide. Générez-en un nouveau et enregistrez-le dans les paramètres.

**« Impossible de défier » un joueur.**
Vérifiez l'orthographe du pseudo et que ce joueur accepte les défis dans ses préférences Lichess.

**« Limite de temps invalide ».**
Choisissez 15, 30, 45 secondes ou un multiple de 60 secondes.
