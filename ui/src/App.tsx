import {useEffect, useState} from 'react'
import {AdapterCard} from "./components/AdapterCard.tsx"
import {AssetList} from "./components/AssetList.tsx";
import {getAdapters} from "./api/adapters.ts";
import SyncMonitor from "./pages/SyncMonitor.tsx";
import {getToken} from "./api/token.ts";
import Login from "./components/Login.tsx";

function App() {
    const [loggedIn, setLoggedIn] = useState<boolean>(!!getToken());

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

    if (!loggedIn) {
        return (
            <Login onLogin={()=> setLoggedIn(true)}/>
        )
    }

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

            <SyncMonitor/>

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
