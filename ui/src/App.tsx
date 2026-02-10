import {useEffect, useState} from 'react'
import {AdapterCard} from "./components/AdapterCard.tsx"
import {AssetList} from "./components/AssetList.tsx";
import {getAdapters} from "./api/adapters.ts";

function App() {
    const [adapters, setAdapters] = useState([])
    const [error, setError] = useState(null)

    useEffect(() => {
        getAdapters()
            .then((res) => {
                setAdapters(res.available)
            })
            .catch((err) => {
                setError(err.message)
            });
    }, [])


    return (
        <div style={{padding: "24px"}}>
            <h1>Adapter System UI</h1>

            {error && <p style={{color: "red"}}>{error}</p>}

            <h2>Available Adapters</h2>
            <div style={styles.grid}>
                {adapters.map((adapter) => (
                    <AdapterCard key={adapter} name={adapter}/>
                ))}

            </div>

            <AssetList/>
        </div>

    )
}

const styles = {
    grid: {
        display: 'flex',
        gap: "16px",
    },
}

export default App
