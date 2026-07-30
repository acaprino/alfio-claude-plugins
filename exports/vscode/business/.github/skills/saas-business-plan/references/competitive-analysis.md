# Analisi della concorrenza

## Le Cinque Forze di Porter applicate al SaaS

- **Minaccia nuovi entranti: ALTA** -- L'infrastruttura cloud (AWS, GCP, Azure) ha abbattuto le barriere d'ingresso. Nascono 400-450 nuove aziende SaaS ogni anno.
- **Potere dei fornitori: BASSO-MODERATO** -- Storage, compute e database sono commoditizzati.
- **Potere degli acquirenti: ALTO** -- Sottoscrizioni mensili rendono facile il cambio. Piattaforme come G2/Capterra permettono confronti trasparenti.
- **Rivalita' di settore: ESTREMAMENTE INTENSA** -- Oltre 15.000 aziende SaaS solo negli USA.
- **Implicazione strategica**: costruisci switching cost tramite integrazioni profonde, dati proprietari e workflow specifici.

## Framework per l'analisi competitiva

### Strategic Group Mapping

Plotta i competitor su due assi strategici (es. prezzo vs. profondita' funzionale, oppure focus SMB vs. Enterprise). Identifica "white space" non occupati.

### Feature Comparison Matrix

Confronta competitor per features, pricing, integrazioni e supporto con scoring ponderato.

### Perceptual Map / Positioning Matrix

Strumento visivo 2x2 dove la dimensione dei cerchi rappresenta il market share relativo.

Come creare una perceptual map efficace:
1. Scegli due attributi determinanti per il buyer (es. facilita' d'uso vs. completezza funzionale)
2. Identifica 6-10 competitor
3. Plottali basandoti su **dati di percezione del cliente** (rating G2, NPS, interviste) -- non sulla tua opinione
4. Aggiungi la tua posizione per ultima
5. I quadranti vuoti rappresentano opportunita' di posizionamento

## Reverse engineering delle strategie competitor

**Pricing intelligence** -- Monitora le pagine prezzi con Visualping (alert automatici entro 24h). Crea un canale Slack #competitor-pricing dove i venditori condividono i prezzi negoziati dai deal reali.

**Messaggistica** -- Iscriviti alle email nurture sequence dei competitor (email personale). Analizza landing page e homepage. Traccia i cambiamenti con Wayback Machine.

**Prodotto** -- Iscriviti ai free trial di tutti i competitor chiave. Monitora changelog e release notes. Traccia le posizioni aperte (hiring di ML engineers = feature AI in arrivo).

**Strategie di crescita** -- SEMrush/Ahrefs per keyword organiche e paid. SimilarWeb per la breakdown completa del traffico (organic, paid, social, referral). BuzzSumo per i contenuti top-performing.

## Analisi sistematica delle recensioni competitor

### Framework "Love / Hate / Want"

1. Raccogli 100+ recensioni recenti per competitor principale da G2, Capterra e TrustRadius
2. Organizzale in un foglio strutturato
3. Categorizza in tre colonne:
   - **Love** -- cosa amano i clienti (feature di adozione)
   - **Hate** -- cosa odiano (la tua arma competitiva)
   - **Want** -- cosa vogliono (domanda non soddisfatta = segnale per la tua roadmap)

Se "onboarding lento" appare come lamentela su 3+ competitor, hai trovato un gap di mercato. Trasforma le lamentele in marketing: recensioni su "onboarding lento" -> la tua promessa "Setup in 24 ore".

## Tool per analisi competitiva

| Tool | Funzione | Costo |
|------|---------|-------|
| **SEMrush** | All-in-one: SEO, PPC, content, competitor | $139,95-449,95/mese |
| **Ahrefs** | Backlink, Content Gap, keyword storici | Da $129/mese |
| **SpyFu** | 10+ anni di storico ads, ad copy, stime di spesa | $39-249/mese |
| **SimilarWeb** | Traffico, market share, audience overlap | Da $149/mese |
| **BuiltWith** | Identificazione tech stack competitor | Free basic; da $295/mese |
| **Crayon/Klue** | Piattaforme CI enterprise con battlecard AI | Enterprise pricing |
| **Visualping** | Monitoraggio automatico modifiche siti web | Da $13/mese (free plan) |
