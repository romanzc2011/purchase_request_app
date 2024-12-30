
const Price = () => {
  return (
    <div className='col-sm-3'>
      <label htmlFor="price" className="col-sm-2 col-form-label">
        <strong>Price</strong>
      </label>
      <div className="col-sm-2">
        <input
          id="price"
          type="text"
          className="form-control"
        />
      </div>
    </div> // Closing the outer <div>
  );
}

export default Price;
