import express from 'express';
import catalogoLibri from './model/catalogo.js';
import clientiFile from './model/clienti.js';
import e from 'express';
import { get } from 'node:http';
import bodyParser from 'body-parser';


const app = express();
app.use(bodyParser.json());
const PORT = 3000;
const BASE_PATH = "/api/v1";
    
var catalogo = [...catalogoLibri];
var clienti = [...clientiFile];

app.listen(PORT, () => {
    console.log("Server attivo sulla porta " + PORT);
});

app.get("/", (req, res) => {
    res.send("Benvenuto nella tua libreria online!");
});

app.get(`${BASE_PATH}/libri`, 
    (req, res) => {res.json(catalogo); 
});

app.get(BASE_PATH + "/clienti", (req, res) => {
    res.json(clienti);
});


// LIBRI
//RICERCA PER TITOLO
app.get(`${BASE_PATH}/libri/search`, (req, res) => {
    let titoloParam = (req.query.titolo||"").toString().trim().toLowerCase();

    if (!titoloParam) return res.status(400).json({ error: "Parametro errato" });

    let results = catalogo.filter(libro => libro.titolo.toLowerCase().includes(titoloParam));

    return res.json(results);
});

//RICERCA PER ID
app.get(`${BASE_PATH}/libri/:id`, (req, res) => {
    let idParam = parseInt(req.params.id);

    let libroTrovato = catalogo.find(libro => libro.id === idParam);

    if (!libroTrovato) {
        return res.status(404).json({ error: "Libro non trovato" });
    } else {
        return res.json(libroTrovato);
    }
});


app.post(`${BASE_PATH}/libri`, (req, res) => {
    const nuovoLibro = req.body;

    if (!validaLibro(nuovoLibro)) {
        return res.status(400).json({ error: "Nessun dato fornito" });
    }

    const maxId = catalogo.map(item => item.id).reduce((a,b) =>Math.max(a,b),0);
    nuovoLibro.id = maxId +1;

    catalogo.push(nuovoLibro);
    return res.status(201).json({ message: "Libro aggiunto con successo"});
});


app.delete(`${BASE_PATH}/libri/:id`, (req, res) => {
    const idParam = parseInt(req.params.id);
    const index = catalogo.findIndex(libro=> libro.id === idParam)
    if (index === -1) {
        return res.status(404).json({ error: "Libro non trovato" });
    }
    catalogo.splice(index, 1)
    res.json({message: 'Libro eliminato con successo'})
});

app.put (`${BASE_PATH}/libri/:id`, (req, res) => {
    const idParam = parseInt(req.params.id);
    let libroAggiornato = req.body;
    if (!validaLibro(libroAggiornato)) {
        return res.status(400).json({ error: "Nessun dato fornito" });
    }
    const index = catalogo.findIndex(libro=> libro.id === idParam);

    if (index === -1) {
        return res.status(404).json({ error: "Libro non trovato" });
    }

    let libroDaAggiornare = catalogo[index];
    catalogo[index] = {...libroDaAggiornare, ...libroAggiornato};

    res.status(200).json({message: 'Libro aggiornato con successo'});
});


function validaLibro(libro) {
    if (libro && libro.titolo && libro.autore && libro.editore)       // autore titolo editore NOT NULL   
        {return true;}
    else
        {return false}
}


// CLIENTI
app.get(`${BASE_PATH}/clienti/search`, (req, res) => {
    let nomeParam = (req.query.nome||"").toString().trim().toLowerCase();

    if (!nomeParam) return res.status(400).json({ error: "Parametro errato" });

    let results = clienti.filter(cliente => cliente.nome.toLowerCase().includes(nomeParam));

    return res.json(results);
});

//RICERCA PER ID
app.get(`${BASE_PATH}/clienti/:id`, (req, res) => {
    let idParam = parseInt(req.params.id);

    let clienteTrovato = clienti.find(cliente => cliente.id === idParam);

    if (!clienteTrovato) {
        return res.status(404).json({ error: "cliente non trovato" });
    } else {
        return res.json(clienteTrovato);
    }
});


app.post(`${BASE_PATH}/clienti`, (req, res) => {
    const nuovoCliente = req.body;

    if (!validaCliente(nuovoCliente)) {
        return res.status(400).json({ error: "Nessun dato fornito" });
    }

    const maxId = clienti.map(item => item.id).reduce((a,b) =>Math.max(a,b),0);
    nuovoCliente.id = maxId +1;

    clienti.push(nuovoCliente);
    return res.status(201).json({ message: "Cliente aggiunto con successo"});
});


app.delete(`${BASE_PATH}/clienti/:id`, (req, res) => {
    const idParam = parseInt(req.params.id);
    const index = clienti.findIndex(cliente=> cliente.id === idParam)
    if (index === -1) {
        return res.status(404).json({ error: "Cliente non trovato" });
    }
    clienti.splice(index, 1)
    res.json({message: 'Cliente eliminato con successo'})
});

app.put (`${BASE_PATH}/clienti/:id`, (req, res) => {
    const idParam = parseInt(req.params.id);
    let clienteAggiornato = req.body;
    if (!validaCliente(clienteAggiornato)) {
        return res.status(400).json({ error: "Nessun dato fornito" });
    }
    const index = clienti.findIndex(cliente=> cliente.id === idParam);

    if (index === -1) {
        return res.status(404).json({ error: "cliente non trovato" });
    }

    let clienteDaAggiornare = clienti[index];
    clienti[index] = {...clienteDaAggiornare, ...clienteAggiornato};

    res.status(200).json({message: 'cliente aggiornato con successo'});
});


function validaCliente(cliente) {
    if (cliente && cliente.nome && cliente.cognome && cliente.eta)       // autore titolo editore NOT NULL   
        {return true;}
    else
        {return false}
}