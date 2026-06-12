import React, { useState, useRef} from 'react';
import JsonRpc from '../../helpers/jsonrpc';
import currencyFormatter from 'currency-formatter';

const jsonRpc = new JsonRpc();

function Consultant(){

    const [barcode, setBarcode] = useState('')
    const [product, setProduct] = useState({})
    const [foundproduct, setFoundProduct] = useState(false)
    const [debounce, setDebounce] = useState(true)
    const barcodeRef = useRef(null);

    // useEffect(() => { }, [])

    function handleSearch(event){
        let params = { 'barcode': barcode }
        if (debounce) {
            jsonRpc._route('/consultant/product/search', params, 'attr').then(res => {
                if(!!res.data.found){
                    setProduct(res.data)
                    setFoundProduct(true)
                    setBarcode('')

                    setTimeout(() => {
                        setFoundProduct(false)
                    }, 7000);
                } else {
                    setFoundProduct(false)
                    setBarcode('')
                    setDebounce(true)
                }
                setDebounce(false);
                setTimeout(() => {
                    setDebounce(true);
                    barcodeRef.current.focus();
                }, 3000);
            })
        }
        event.preventDefault();
    }

    return (
        <div className="container">
            <div className="row o_row_consultant">
                <div className="col-lg-12">
                    <h3>Consulte aquí el precio de su articulo</h3>
                </div>
                <div className="col-lg-12">
                    {/* Buscador */}
                    <form className="o_container_consultant" style={{marginBottom: '0px'}} name="searchForm" onSubmit={handleSearch}>
                        <div className="input-group mb-3">
                            <input
                              className="form-control oe_search_box border-0 text-bg-light"
                              type="text"
                              name="barcode"
                              placeholder="Buscar..."
                              autoFocus
                              required
                              value={barcode}
                              onChange={e => setBarcode(e.target.value)}
                              disabled={!debounce}
                              ref={barcodeRef}
                              />
                        </div>
                    </form>
                    {/* Resumen del producto */}
                    {!!foundproduct ?
                    <div>
                        <form className="o_container_product_info">
                            <div className="row">
                                <div className="col-lg-5">
                                    <img
                                      src={product.image}
                                      className="rounded mx-auto d-block image_product d-none d-lg-block"
                                      alt="Image not found"
                                      />
                                </div>
                                <div className="col-lg-7 section-product-info">
                                    <table className="table table-borderless table-product-info">
                                        <tbody>
                                            <tr className="line">
                                                <th scope="row">Producto</th>
                                                <td>{product.name}</td>
                                            </tr>
{                                           
                                            // <tr>
                                            //     <th scope="row">Precio REF</th>
                                            //     <td>
                                            //         {currencyFormatter.format(product.price, {
                                            //             code: product.currency[0],
                                            //             symbol: product.currency[1],
                                            //             format: '%s %v',
                                            //         })}
                                            //     </td>
                                            // </tr>
                                            // <tr>
                                            //     <th scope="row">Impuestos</th>
                                            //     {product.tax[0] == 0.0 ?
                                            //       <td>Exento</td>
                                            //     :
                                            //     <td>
                                            //       ({product.tax[0]},00 %) {
                                            //         currencyFormatter.format(product.tax[1], {
                                            //             code: product.currency[0],
                                            //             symbol: product.currency[1],
                                            //             format: '%s %v',
                                            //         })
                                            //       }
                                            //     </td>
                                            //     }
                                            // </tr>
}
                                            <tr>
                                                <th scope="row">REF</th>
                                                <td className="price">
                                                    {currencyFormatter.format(product.total, {
                                                        code: product.currency[0],
                                                        symbol: product.currency[1],
                                                        format: '%s %v',
                                                    })}
                                                </td>
                                            </tr>
                                            <tr className="line">
                                                <th scope="row">Precio {product.foreign_currency[0]}</th>
                                                <td className="price">
                                                    {currencyFormatter.format(product.price_currency, {
                                                        code: product.foreign_currency[0],
                                                        symbol: product.foreign_currency[1],
                                                        format: '%s %v',
                                                    })}
                                                </td>
                                            </tr>
                                            {!!product.alt_price ?
                                                <tr>
                                                    <th scope="row">Precio especial</th>
                                                    <td className="price price-red">
                                                        {currencyFormatter.format(product.alt_price, {
                                                            code: product.currency[0],
                                                            symbol: product.currency[1],
                                                            format: '%s %v',
                                                        })}
                                                    </td>
                                                </tr>
                                            :null}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </form>
                    </div>
                    :
                    <div className="product_not_found">
                        <p>Sin resultados.</p>
                    </div>
                    }
                </div>
            </div>
        </div>
    )
}

export default Consultant