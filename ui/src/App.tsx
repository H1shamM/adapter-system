import {useState} from 'react'
import {getToken} from "./api/token.ts";
import Login from "./components/Login.tsx";
import Dashboard from './pages/Dashboard.tsx';

function App() {
    const [loggedIn, setLoggedIn] = useState<boolean>(!!getToken("access"));

    if (!loggedIn) {
        return (
            <Login onLogin={()=> setLoggedIn(true)}/>
        )
    }

    return (
        <Dashboard/>
    )
}

export default App
