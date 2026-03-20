const fs = require('fs');

function simulate() {
    const originalJsonString = JSON.stringify({
        data: {
            transacciones: [
                { id: 1, movimientos_contables: [{ cuenta_codigo: "51159501" }] },
                { id: 2, movimientos_contables: [{ cuenta_codigo: "OTRA" }] }
            ]
        },
        signature: "abc"
    });

    const jsonData = JSON.parse(originalJsonString);
    let rawDocs = jsonData.transacciones || jsonData.documentos;
    if (!rawDocs && jsonData.data) {
        rawDocs = jsonData.data.transacciones || jsonData.data.documentos;
    }
    jsonData.documentos = rawDocs;
    const transformData = jsonData;

    // Simulate transform
    let documentosAProcesar = JSON.parse(JSON.stringify(transformData.documentos));
    // filter out docs
    let documentosTransformados = [documentosAProcesar[0]];

    const newBackupData = {
        ...transformData,
        ...(transformData.data ? {
            data: {
                ...transformData.data,
                transacciones: documentosTransformados,
                documentos: documentosTransformados
            },
            signature: "MODIFIED_INVALID_SIGNATURE"
        } : {
            transacciones: documentosTransformados,
            documentos: documentosTransformados
        })
    };

    console.log("Keys in newBackupData:", Object.keys(newBackupData));
    console.log("Length of newBackupData.documentos (root):", newBackupData.documentos.length);
    console.log("Length of newBackupData.data.transacciones:", newBackupData.data.transacciones.length);
}

simulate();
