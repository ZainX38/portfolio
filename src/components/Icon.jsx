function Icon({ className, iconRef }) {
    return (
        <svg aria-hidden="true" className={`block ${className}`}>
            <use href={iconRef}/>
        </svg>
    )
}

export default Icon;