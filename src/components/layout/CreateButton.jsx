import Icon from './Icon.jsx';

function CreateButton({ name, link, icon, className }) {
    return (
        <a 
            key={name} 
            href={link} 
            target='_blank'
            rel="noopener noreferrer"
            className={className}>
                <Icon 
                className="w-4 h-4" 
                iconRef={icon} />
                {name}
        </a>
)
}

export default CreateButton