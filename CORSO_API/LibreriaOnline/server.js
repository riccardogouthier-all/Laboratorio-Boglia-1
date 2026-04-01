import express from 'express';
import catalogoLibri from './model/catalogo.js';
import clientiFile from './model/clienti.js';


const app = express();
const PORT = 3000;
const BASE_PATH = "/api/v1";

var catalogo = catalogoLibri;
var clienti = clientiFile;

app.listen(PORT, () => {
    console.log("Server attivo sulla porta " + PORT);
});

app.get("/", (req, res) => {
    res.send("Benvenuto nella tua libreria online!");
});

app.get(BASE_PATH + "/catalogo", (req, res) => {
    res.json(catalogo);
});

app.get(BASE_PATH + "/clienti", (req, res) => {
    res.json(clienti);
});